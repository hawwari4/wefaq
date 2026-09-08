from flask import Blueprint, jsonify, request
from sqlalchemy import and_, or_

from models import CompatibilityRequest, Notification, SavedCandidate, User, db
from security import get_user_by_code
from services.matching_service import _candidate_summary, evaluate_eligibility, score_pair


match_interaction_bp = Blueprint('match_interactions', __name__, url_prefix='/api/matching')


def _approved_user():
    user = get_user_by_code()
    if not user:
        return None, (jsonify({'success': False, 'message': 'يلزم تسجيل الدخول للوصول إلى هذه الصفحة.'}), 403)
    if user.status != 'approved':
        return None, (jsonify({'success': False, 'message': 'تتاح هذه الميزة بعد اعتماد الطلب.'}), 403)
    return user, None


def _eligible_candidate(owner, candidate_id):
    if candidate_id == owner.id:
        return None, (jsonify({'success': False, 'message': 'لا يمكنك اختيار حسابك.'}), 400)
    candidate = User.query.get(candidate_id)
    if not candidate:
        return None, (jsonify({'success': False, 'message': 'المرشح غير متاح.'}), 404)
    eligibility = evaluate_eligibility(owner, candidate, allowed_statuses=('approved',))
    if not eligibility['eligible']:
        return None, (jsonify({'success': False, 'message': 'هذا المرشح غير متاح للتوافق حالياً.'}), 400)
    return candidate, None


def _interaction_candidate(viewer, candidate):
    if not candidate or candidate.status != 'approved':
        return {'available': False, 'candidate': None, 'compatibility_percentage': None}
    eligibility = evaluate_eligibility(viewer, candidate, allowed_statuses=('approved',))
    if not eligibility['eligible']:
        return {'available': False, 'candidate': None, 'compatibility_percentage': None}
    score = score_pair(viewer, candidate, allowed_statuses=('approved',))
    return {
        'available': True,
        'candidate': _candidate_summary(candidate, private=True),
        'compatibility_percentage': score['compatibility_percentage'] if score['has_sufficient_data'] else None,
    }


def _request_payload(item, viewer, direction):
    candidate = item.receiver if direction == 'sent' else item.sender
    return {
        'id': item.id,
        'direction': direction,
        'status': item.status,
        'created_at': item.created_at.isoformat(),
        'updated_at': item.updated_at.isoformat(),
        **_interaction_candidate(viewer, candidate),
    }


@match_interaction_bp.route('/requests', methods=['GET'])
def list_requests():
    user, error = _approved_user()
    if error:
        return error
    rows = CompatibilityRequest.query.filter(
        or_(CompatibilityRequest.sender_id == user.id, CompatibilityRequest.receiver_id == user.id)
    ).order_by(CompatibilityRequest.updated_at.desc()).all()
    incoming = [_request_payload(item, user, 'incoming') for item in rows if item.receiver_id == user.id]
    sent = [_request_payload(item, user, 'sent') for item in rows if item.sender_id == user.id]
    return jsonify({'success': True, 'incoming': incoming, 'sent': sent}), 200


@match_interaction_bp.route('/requests', methods=['POST'])
def create_request():
    user, error = _approved_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    try:
        candidate_id = int(data.get('candidate_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'المرشح غير صالح.'}), 400
    candidate, error = _eligible_candidate(user, candidate_id)
    if error:
        return error

    existing = CompatibilityRequest.query.filter(or_(
        and_(CompatibilityRequest.sender_id == user.id, CompatibilityRequest.receiver_id == candidate.id),
        and_(CompatibilityRequest.sender_id == candidate.id, CompatibilityRequest.receiver_id == user.id),
    )).first()
    if existing:
        message = 'لديك طلب وارد من هذا المرشح.' if existing.receiver_id == user.id and existing.status == 'pending' else 'سبق تسجيل طلب توافق لهذا المرشح.'
        return jsonify({'success': True, 'message': message, 'request': _request_payload(existing, user, 'incoming' if existing.receiver_id == user.id else 'sent')}), 200

    item = CompatibilityRequest(sender_id=user.id, receiver_id=candidate.id, status='pending')
    db.session.add(item)
    db.session.add(Notification(user_id=candidate.id, message='لديك طلب توافق جديد.'))
    db.session.commit()
    return jsonify({'success': True, 'message': 'تم إرسال طلب التوافق.', 'request': _request_payload(item, user, 'sent')}), 201


@match_interaction_bp.route('/requests/<int:request_id>', methods=['PUT'])
def update_request(request_id):
    user, error = _approved_user()
    if error:
        return error
    item = CompatibilityRequest.query.get(request_id)
    if not item:
        return jsonify({'success': False, 'message': 'طلب التوافق غير موجود.'}), 404
    if item.receiver_id != user.id:
        return jsonify({'success': False, 'message': 'لا يمكنك تعديل هذا الطلب.'}), 403
    if item.status != 'pending':
        return jsonify({'success': False, 'message': 'تمت معالجة هذا الطلب من قبل.'}), 409
    status = (request.get_json(silent=True) or {}).get('status')
    if status not in ('accepted', 'declined'):
        return jsonify({'success': False, 'message': 'حالة الطلب غير صالحة.'}), 400
    item.status = status
    notice = 'تم قبول طلب التوافق الذي أرسلته.' if status == 'accepted' else 'تم الاعتذار عن طلب التوافق الذي أرسلته.'
    db.session.add(Notification(user_id=item.sender_id, message=notice))
    db.session.commit()
    return jsonify({'success': True, 'message': 'تم قبول الطلب.' if status == 'accepted' else 'تم رفض الطلب.', 'request': _request_payload(item, user, 'incoming')}), 200


@match_interaction_bp.route('/saved', methods=['GET'])
def list_saved_candidates():
    user, error = _approved_user()
    if error:
        return error
    rows = SavedCandidate.query.filter_by(user_id=user.id).order_by(SavedCandidate.created_at.desc()).all()
    saved = [{
        'id': item.id,
        'candidate_ref': item.candidate_id,
        'created_at': item.created_at.isoformat(),
        **_interaction_candidate(user, item.candidate),
    } for item in rows]
    return jsonify({'success': True, 'saved': saved}), 200


@match_interaction_bp.route('/saved', methods=['POST'])
def save_candidate():
    user, error = _approved_user()
    if error:
        return error
    data = request.get_json(silent=True) or {}
    try:
        candidate_id = int(data.get('candidate_id'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'المرشح غير صالح.'}), 400
    candidate, error = _eligible_candidate(user, candidate_id)
    if error:
        return error
    item = SavedCandidate.query.filter_by(user_id=user.id, candidate_id=candidate.id).first()
    if not item:
        item = SavedCandidate(user_id=user.id, candidate_id=candidate.id)
        db.session.add(item)
        db.session.commit()
    return jsonify({'success': True, 'message': 'تم حفظ المرشح.', 'saved_id': item.id}), 200


@match_interaction_bp.route('/saved/<int:candidate_id>', methods=['DELETE'])
def remove_saved_candidate(candidate_id):
    user, error = _approved_user()
    if error:
        return error
    item = SavedCandidate.query.filter_by(user_id=user.id, candidate_id=candidate_id).first()
    if not item:
        return jsonify({'success': False, 'message': 'المرشح غير موجود في المحفوظات.'}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'تمت إزالة المرشح من المحفوظات.'}), 200
