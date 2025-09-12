import logging
import time

from src.core import evidence_store
from src.mail_parser.processor import EmailEvidenceProcessor

logger = logging.getLogger('worker_tasks')


def process_uploaded_mbox(tmp_path, config_path='config.json'):
    """Background worker task to process uploaded mbox and save generated evidences into DB.

    This function is intended to be queued by RQ and run by a worker process.
    It will instantiate EmailEvidenceProcessor, load the mbox, and for each message call the evidence generator.
    """
    try:
        logger.info(f'Start processing uploaded mbox: {tmp_path}')
        proc = EmailEvidenceProcessor(config_path)
        proc.load_mbox(tmp_path)
        messages = proc.get_all_message_metadata()
        results = []

        for m in messages:
            # For simplicity, convert mbox key -> message and call evidence generator
            try:
                msg = proc.mbox[proc.metadata_map[m['id']]['key']]
                evidence_number = proc.evidence_generator.get_evidence_number(
                    '갑') if hasattr(proc, 'evidence_generator') else '갑 제1호증'
                eg_result = proc.evidence_generator.process_email_to_evidence(
                    msg, evidence_number)
                results.append(eg_result)
            except Exception as e:
                logger.exception(
                    f'Failed processing message {m.get("id")}: {e}')

        logger.info(
            f'Processing complete for {tmp_path}, produced {len(results)} evidences')
        return {'status': 'completed', 'count': len(results)}
    except Exception as e:
        logger.exception(f'Worker failed: {e}')
        return {'status': 'failed', 'error': str(e)}
